"""Rock Slinger re-rig: the pose solver (numpy).

A pose is a rigid world-space delta per bone, D = (R, t): a rest point x of that bone goes to R x + t (armature space).
Skinning is sum_b w_b D_b(x); Blender's pose-bone basis follows from the rest matrices (to_basis).
The body is driven by a few controls (pelvis, chest and head turns, wrist and foot targets, elbow / knee poles);
the helper bones (half-turn and twist bones) are derived, so every clip keys them consistently.
"""
import numpy as np
from scipy.spatial.transform import Rotation as Rot
import rs_skel

J = rs_skel.J
I3 = np.eye(3)


# ------------------------------------------------------------------------------------------------ small maths
def unit(v):
    v = np.asarray(v, float)
    return v / max(np.linalg.norm(v), 1e-12)


def perp(v, axis):
    """v without its component along the unit vector axis, normalised."""
    v = np.asarray(v, float)
    return unit(v - (v @ axis) * axis)


def rx(deg): return Rot.from_euler('x', deg, degrees=True).as_matrix()
def ry(deg): return Rot.from_euler('y', deg, degrees=True).as_matrix()
def rz(deg): return Rot.from_euler('z', deg, degrees=True).as_matrix()


def axis_angle(axis, deg):
    return Rot.from_rotvec(unit(axis) * np.radians(deg)).as_matrix()


def from_to(a, b):
    """The least rotation taking unit a onto unit b."""
    a, b = unit(a), unit(b)
    c = float(np.clip(a @ b, -1, 1))
    if c > 1 - 1e-12: return I3.copy()
    if c < -1 + 1e-9:
        o = perp(np.array([1.0, 0, 0]) if abs(a[0]) < 0.9 else np.array([0, 1.0, 0]), a)
        return Rot.from_rotvec(o * np.pi).as_matrix()
    ax = np.cross(a, b)
    return Rot.from_rotvec(unit(ax) * np.arccos(c)).as_matrix()


def frame(y, f):
    """Orthonormal frame with y along the bone and f (made perpendicular) as its second axis."""
    y = unit(y); f = perp(f, y)
    return np.column_stack([f, y, np.cross(f, y)])


def power(R, k):
    return Rot.from_rotvec(Rot.from_matrix(R).as_rotvec() * k).as_matrix()


def slerp(Ra, Rb, k):
    return Ra @ power(Ra.T @ Rb, k)


def swing_twist(R, axis):
    """R = S T with T a turn about `axis` (unit) and S a swing that turns `axis` the least way."""
    q = Rot.from_matrix(R).as_quat()          # x y z w
    p = (q[:3] @ axis) * axis
    t = np.array([p[0], p[1], p[2], q[3]])
    n = np.linalg.norm(t)
    T = I3.copy() if n < 1e-9 else Rot.from_quat(t / n).as_matrix()
    return R @ T.T, T


def twist_angle(T, axis):
    rv = Rot.from_matrix(T).as_rotvec()
    return float(np.degrees(rv @ axis))


def ypr(yaw=0.0, pitch=0.0, roll=0.0):
    """World turn: yaw about +Z (positive = to his left), pitch about +X (positive = lean back... see below), roll about +Y.
    He faces -Y: pitch > 0 tips the top forward (toward -Y); roll > 0 tips the top to his left (+X)."""
    return rz(yaw) @ rx(pitch) @ ry(roll)


class D:
    """Rigid delta x -> R x + t (optionally with a scale about a pivot, for the stone)."""
    __slots__ = ('R', 't', 's')

    def __init__(self, R=None, t=None, s=1.0):
        self.R = I3.copy() if R is None else np.asarray(R, float)
        self.t = np.zeros(3) if t is None else np.asarray(t, float)
        self.s = s

    @staticmethod
    def about(R, rest_pivot, posed_pivot, s=1.0):
        R = np.asarray(R, float)
        return D(R, np.asarray(posed_pivot, float) - s * (R @ np.asarray(rest_pivot, float)), s)

    def __call__(self, x):
        return self.s * (np.asarray(x, float) @ self.R.T) + self.t

    def mat(self):
        M = np.eye(4); M[:3, :3] = self.R * self.s; M[:3, 3] = self.t
        return M


# ------------------------------------------------------------------------------------------------ controls
def default_controls():
    c = dict(
        pelvis=J['pelvis'].copy(), pelvis_rot=I3.copy(), chest_rot=I3.copy(), head_rot=I3.copy(), spine_k=0.5, neck_k=0.5,
        stone=1.0, sling=None,
    )
    for s in 'LR':
        sg = 1.0 if s == 'L' else -1.0
        c['arm.' + s] = dict(wrist=J['wrist.' + s].copy(), pole=_rest_pole(J['shoulder.' + s], J['elbow.' + s], J['wrist.' + s]), aim=None, roll=0.0,
                             shrug=None, protract=None, clav_auto=0.0)
        c['leg.' + s] = dict(ball=J['ball.' + s].copy(), yaw=0.0, lift=0.0, roll=0.0, pole=_rest_pole(J['hip.' + s], J['knee.' + s], J['ankle.' + s]), toe=None)
    return c


def _rest_pole(a, b, c):
    """Where the middle joint of the rest chain a-b-c points, off the line a-c."""
    return perp(b - a, unit(c - a))


ARM_FOLD = np.array([0.0, -1.0, 0.0])      # the elbow folds the forearm forward (biceps side)
LEG_FOLD = np.array([0.0, 1.0, 0.0])       # the knee folds the shin back
FOLD_MAX = {'arm': 148.0, 'leg': 140.0}


def hinge_ik(S, Wt, j0, j1, j2, fold, pole, fold_max=148.0):
    """Two bones with a true hinge between them, from the rest joints j0-j1-j2.

    The hinge's axis is fixed in the near bone (it is the anatomical one: across the limb, so that the far bone folds
    toward `fold`); whatever sideways lean the sculpt gave the far bone stays with it. At the rest joint positions the
    result is the bind pose itself (no turn at all), and the near bone's roll is never free: it follows from where the
    middle joint points (`pole`). Returns (R_near, R_far, middle joint, end joint, fold angle in degrees, out of reach).
    """
    u = unit(j1 - j0); a = np.linalg.norm(j1 - j0); v = j2 - j1; b = np.linalg.norm(v)
    f = perp(fold, u); h = np.cross(u, f)
    A = u @ v; B = u @ np.cross(h, v)
    R = np.hypot(A, B); phi = np.arctan2(B, A)
    d = np.linalg.norm(Wt - S)
    dmax = np.sqrt(a * a + b * b + 2 * a * R) * 0.9995
    tmax = np.radians(fold_max)
    dmin = np.sqrt(max(a * a + b * b + 2 * a * R * np.cos(tmax - phi), 1e-8))
    dc = float(np.clip(d, dmin, dmax))
    C = (dc * dc - a * a - b * b) / (2 * a)
    theta = phi + np.arccos(np.clip(C / R, -1.0, 1.0))
    Rh = Rot.from_rotvec(h * theta).as_matrix()
    w = a * u + Rh @ v
    n = unit(Wt - S) if d > 1e-9 else unit(w)
    R0 = from_to(w, n)
    e0 = (R0 @ u) - ((R0 @ u) @ n) * n
    pp = np.asarray(pole, float) - (np.asarray(pole, float) @ n) * n
    if np.linalg.norm(e0) > 1e-6 and np.linalg.norm(pp) > 1e-6:
        e0 = unit(e0); pp = unit(pp)
        psi = np.arctan2(n @ np.cross(e0, pp), e0 @ pp)
        Ru = Rot.from_rotvec(n * psi).as_matrix() @ R0
    else:
        Ru = R0
    Rf = Ru @ Rh
    E = S + Ru @ (a * u)
    return Ru, Rf, E, E + Rf @ v, np.degrees(theta), (d > dmax + 1e-6) or (d < dmin - 1e-6), Ru @ Rot.from_rotvec(h * theta * 0.5).as_matrix()


def solve(c):
    """controls -> {bone name: D}, plus info (reach flags, joint positions)."""
    P = {}; info = {'over': []}
    # ---- trunk
    Rp = c['pelvis_rot']
    P['root'] = D.about(Rp, J['pelvis'], c['pelvis'])
    Rc = c['chest_rot']
    Rs = slerp(Rp, Rc, c['spine_k'])
    P['spine'] = D.about(Rs, J['spine'], P['root'](J['spine']))
    P['chest'] = D.about(Rc, J['chest'], P['spine'](J['chest']))
    Rh = c['head_rot']
    Rn = slerp(Rc, Rh, c['neck_k'])
    P['neck'] = D.about(Rn, J['neck'], P['chest'](J['neck']))
    P['head'] = D.about(Rh, J['head'], P['neck'](J['head']))
    # ---- arms
    for s in 'LR':
        sg = 1.0 if s == 'L' else -1.0
        A = c['arm.' + s]
        sh, el, wr, he = J['shoulder.' + s], J['elbow.' + s], J['wrist.' + s], J['hand_end.' + s]
        a = np.linalg.norm(el - sh); b = np.linalg.norm(wr - el)
        Wt = np.asarray(A['wrist'], float)
        if A.get('space') == 'chest': Wt = P['chest'](Wt)
        # clavicle: lifts when the hand goes up, comes forward when it reaches forward or across (in the chest's frame)
        S0 = P['chest'](sh)
        dl = Rc.T @ (Wt - S0); dist = np.linalg.norm(dl); dl = dl / max(dist, 1e-9)
        k = A['clav_auto'] * np.clip(dist / (a + b), 0.0, 1.0)
        shrug = k * 22.0 * np.clip((dl[2] + 0.35) / 1.2, 0.0, 1.0) ** 1.3
        prot = k * (11.0 * np.clip(-dl[1], -0.7, 1.0) + 7.0 * np.clip(-sg * dl[0], 0.0, 1.0))
        if A['shrug'] is not None: shrug = shrug + A['shrug']
        if A['protract'] is not None: prot = prot + A['protract']
        Rcl = Rc @ rz(-sg * prot) @ ry(-sg * shrug)
        P['clavicle.' + s] = D.about(Rcl, J['clav.' + s], P['chest'](J['clav.' + s]))
        S = P['clavicle.' + s](sh)
        pv = Rc @ np.asarray(A['pole'], float) if A.get('space') == 'chest' else A['pole']
        Ru, Rf, E, W, fold, over, Rhalf = hinge_ik(S, Wt, sh, el, wr, ARM_FOLD, pv, FOLD_MAX['arm'])
        if over: info['over'].append('arm.' + s)
        yf = unit(W - E)
        P['upperarm.' + s] = D.about(Ru, sh, S)
        P['forearm.' + s] = D.about(Rf, el, E)
        # hand: follows the forearm, optionally rolled about it and aimed (the fist's axis toward a world direction)
        Rhd = axis_angle(yf, A['roll']) @ Rf if A['roll'] else Rf
        if A['aim'] is not None:
            h0 = Rhd @ unit(he - wr)
            Rhd = from_to(h0, unit(A['aim'])) @ Rhd
        P['hand.' + s] = D.about(Rhd, wr, W)
        # helpers
        Q = Rcl.T @ Ru
        Sw, Tw = swing_twist(Q, unit(el - sh))
        P['shoulder_half.' + s] = D.about(Rcl @ power(Sw, 0.5), sh, S)
        P['upperarm_sw.' + s] = D.about(Rcl @ Sw, sh, S)
        mid = sh + (el - sh) * 0.5
        P['upperarm_tw.' + s] = D.about(Rcl @ Sw @ power(Tw, 0.5), mid, P['upperarm.' + s](mid))
        P['elbow_half.' + s] = D.about(Rhalf, el, E)
        Qh = Rf.T @ Rhd
        _, Th = swing_twist(Qh, unit(wr - el))
        ftw = el + (wr - el) * 0.55
        P['forearm_tw.' + s] = D.about(Rf @ power(Th, 0.5), ftw, P['forearm.' + s](ftw))
        info['elbow.' + s] = E; info['wrist.' + s] = W; info['shoulder.' + s] = S
        info['twist.' + s] = twist_angle(Tw, unit(el - sh)); info['elbow_deg.' + s] = fold
        info['swing.' + s] = np.degrees(np.linalg.norm(Rot.from_matrix(Sw).as_rotvec()))
    # ---- legs
    for s in 'LR':
        Lg = c['leg.' + s]
        hp, kn, an, ba = J['hip.' + s], J['knee.' + s], J['ankle.' + s], J['ball.' + s]
        a = np.linalg.norm(kn - hp); b = np.linalg.norm(an - kn)
        Rft = rz(Lg['yaw']) @ ry(Lg['roll']) @ rx(Lg['lift'])
        ball = np.asarray(Lg['ball'], float)
        P['foot.' + s] = D.about(Rft, ba, ball)
        toe = Lg['toe'] if Lg['toe'] is not None else 0.0
        P['toe.' + s] = D.about(rz(Lg['yaw']) @ rx(toe), ba, ball)
        At = P['foot.' + s](an)
        H = P['root'](hp)
        Rt, Rsn, K, Aa, fold, over, Rhalf = hinge_ik(H, At, hp, kn, an, LEG_FOLD, Lg['pole'], FOLD_MAX['leg'])
        if over:
            info['over'].append('leg.' + s)
            # the foot goes with the leg (it cannot stay planted)
            P['foot.' + s] = D.about(Rft, an, Aa); P['toe.' + s] = D.about(P['toe.' + s].R, ba, P['foot.' + s](ba))
        P['thigh.' + s] = D.about(Rt, hp, H)
        P['shin.' + s] = D.about(Rsn, kn, K)
        P['knee_half.' + s] = D.about(Rhalf, kn, K)
        info['knee.' + s] = K; info['knee_deg.' + s] = fold
    # ---- sling: a chain of nodes from the grip (world positions given, or hanging rigidly from the hand)
    nodes = rs_skel.sling_nodes(); Sg = rs_skel.SLING_SEGS
    names = ['sling'] + ['sling.%03d' % i for i in range(1, Sg)]
    grip = P['hand.R'](nodes[0])
    Rprev = P['hand.R'].R; pos = grip
    tgt = c.get('sling')
    for i in range(Sg):
        ur = unit(nodes[i + 1] - nodes[i])
        if tgt is None:
            Ri = Rprev
        else:
            up = unit(np.asarray(tgt[i + 1], float) - np.asarray(tgt[i], float))
            Ri = from_to(Rprev @ ur, up) @ Rprev
        P[names[i]] = D.about(Ri, nodes[i], pos)
        pos = P[names[i]](nodes[i + 1]); Rprev = Ri
    P['stone'] = D.about(Rprev, J['pouch'], pos, s=max(float(c.get('stone', 1.0)), 1e-4))
    info['grip'] = grip; info['pouch'] = pos
    return P, info


# ------------------------------------------------------------------------------------------------ skinning / export
def skin(V, W, names, P):
    out = np.zeros_like(V)
    for i, nme in enumerate(names):
        w = W[:, i]
        m = w > 0
        if m.any():
            out[m] += w[m, None] * P[nme](V[m])
    return out


def to_basis(P, rest, parents):
    """{bone: 4x4 pose-bone basis} from the deltas, Blender's rest matrices (armature space) and the parent table."""
    out = {}
    for nme, d in P.items():
        Rb = rest[nme]
        Dm = d.mat()
        par = parents[nme]
        if par:
            Dm = np.linalg.inv(P[par].mat()) @ Dm
        out[nme] = np.linalg.inv(Rb) @ Dm @ Rb
    return out
