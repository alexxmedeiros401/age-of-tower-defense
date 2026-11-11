"""Rock Slinger re-rig: skin weights.

  labels (one main bone per vertex, rs_labels)  ->  surface blur (narrow at hinges, wide round the trunk, shoulders, hips)
  ->  helper bones take their share (half-turn bones in the joints' blend zones, twist bones along the arms)
  ->  sling and stone  ->  at most 4 bones per vertex.
"""
import colorsys
import numpy as np
from scipy.sparse import diags
from scipy.sparse.linalg import splu
import rs_skel, rs_labels

J = rs_skel.J


def blur(mesh, verts, P, std):
    """Heat-diffuse the columns of P over the surface; a step edge spreads to about +-1.3 std (10%..90%)."""
    L, area = mesh.laplacian()
    L = L[verts][:, verts].tocsc(); A = diags(area[verts])
    t = std * std / 2.0
    lu = splu((A + t * L).tocsc())
    out = np.column_stack([lu.solve(area[verts] * P[:, k]) for k in range(P.shape[1])])
    out = np.clip(out, 0, None)
    return out / np.maximum(out.sum(1, keepdims=True), 1e-12)


def smoothstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def axial(P, a, b):
    ab = b - a
    return ((P - a) @ ab) / (ab @ ab)


def region_masks(mesh, verts, col):
    """Props on the trunk: the hip bag (with its stones) and the belt knot with its tails."""
    P = mesh.V[verts]; C = col[verts]
    hsv = np.array([colorsys.rgb_to_hsv(*c) for c in C])
    yellow = (hsv[:, 0] * 360 > 26) & (hsv[:, 1] > 0.6) & (hsv[:, 2] > 0.5)
    bag = (~yellow) & (P[:, 0] > -0.50) & (P[:, 0] < -0.17) & (P[:, 1] < -0.09) & (P[:, 2] > 0.63) & (P[:, 2] < 0.955)
    knot = (~yellow) & (P[:, 0] > -0.02) & (P[:, 0] < 0.22) & (P[:, 1] < -0.265) & (P[:, 2] > 0.60) & (P[:, 2] < 0.94)
    return bag, knot, yellow


def compute(mesh, col, dist, vis, opts=None):
    o = dict(std_narrow=0.028, std_wide=0.070, std_mask=0.05, half_gain=1.0)
    o.update(opts or {})
    B = rs_skel.bones()
    names = [b[0] for b in B]
    main_names = [b[0] for b in B if b[4] == 'main']
    nm = {n: i for i, n in enumerate(main_names)}
    verts, lab, info = rs_labels.segment(mesh, col, dist, vis, main_names)
    P = mesh.V[verts]; G = info['G']
    n = len(verts)

    # ---- label fixes -------------------------------------------------------------------------------------------
    bag, knot, yellow = region_masks(mesh, verts, col)
    head = lab == nm['head']
    # everything above the middle of the head is head (the bones in his hair)
    limb = np.zeros(n, bool)
    for k in info['grp']: limb |= info['grp'][k]
    head |= (P[:, 2] > J['head'][2] + 0.22) & ~limb
    lab[head] = nm['head']
    # the skirt hangs from the pelvis: thighs only own what lies below the hips and beside the middle
    for s in 'LR':
        th = lab == nm['thigh.' + s]
        back_to_root = th & ((P[:, 2] > J['hip.' + s][2] - 0.03) | (np.abs(P[:, 0]) < 0.055))
        lab[back_to_root] = nm['root']
    lab[bag | knot] = nm['root']
    lab = rs_labels.mode_filter(G, lab, len(main_names), 1, frozen=(bag | knot | head))

    # ---- blur --------------------------------------------------------------------------------------------------
    onehot = np.zeros((n, len(main_names))); onehot[np.arange(n), lab] = 1.0
    Wn = blur(mesh, verts, onehot, o['std_narrow'])
    Ww = blur(mesh, verts, onehot, o['std_wide'])
    wide_bones = ['root', 'spine', 'chest', 'clavicle.L', 'clavicle.R', 'thigh.L', 'thigh.R']
    m = np.isin(lab, [nm[b] for b in wide_bones]).astype(float)
    # the upper arm: wide at the shoulder, narrow at the elbow
    for s in 'LR':
        ua = lab == nm['upperarm.' + s]
        t = axial(P, J['shoulder.' + s], J['elbow.' + s])
        m[ua] = 1.0 - smoothstep(t[ua], 0.35, 0.8)
    m = _blur_scalar(mesh, verts, m, o['std_mask'])
    W = Wn * (1 - m[:, None]) + Ww * m[:, None]
    # rigid props
    rigid_root = bag | knot
    W[rigid_root] = 0.0; W[rigid_root, nm['root']] = 1.0
    W[:, :] = W / W.sum(1, keepdims=True)

    full = {nme: np.zeros(n) for nme in names}
    for i, nme in enumerate(main_names): full[nme] = W[:, i].copy()

    # ---- neck: the head's blend zone with the trunk ----------------------------------------------------------------
    a = full['head']; b = full['chest'] + full['clavicle.L'] + full['clavicle.R'] + full['spine']
    share = np.minimum(a, b) * 1.6
    share = np.minimum(share, a + b)
    tot = np.maximum(a + b, 1e-9)
    for k in ('head',): full[k] -= share * a / tot
    for k in ('chest', 'clavicle.L', 'clavicle.R', 'spine'): full[k] -= share * full[k] / np.maximum(b, 1e-9) * (b / tot)
    full['neck'] = share

    # ---- arms: half-turn bones and twist bones -----------------------------------------------------------------------
    for s in 'LR':
        sh, el, wr = J['shoulder.' + s], J['elbow.' + s], J['wrist.' + s]
        ua = full['upperarm.' + s].copy(); fa = full['forearm.' + s].copy(); hd = full['hand.' + s]
        trunk = full['chest'] + full['clavicle.' + s] + full['spine'] + full['neck'] + full['head'] + full['root'] + full['clavicle.' + ('R' if s == 'L' else 'L')]
        # shoulder: the zone blended between trunk and arm gives 2 min(a, b) to the half-swing bone
        arm_all = ua + fa + hd
        hs = np.minimum(2.0 * np.minimum(trunk, arm_all) * o['half_gain'], trunk + arm_all)
        tu = axial(P, sh, el)
        hs *= 1.0 - smoothstep(tu, 0.75, 1.1)                       # none of it down by the elbow
        tt = np.maximum(trunk + arm_all, 1e-9)
        ft = hs * trunk / tt; fa_ = hs * arm_all / tt
        for k in ('chest', 'clavicle.L', 'clavicle.R', 'spine', 'neck', 'head', 'root'):
            full[k] -= ft * full[k] / np.maximum(trunk, 1e-9)
        ua_share = ua / np.maximum(arm_all, 1e-9)
        ua = ua - fa_ * ua_share
        fa = fa - fa_ * fa / np.maximum(arm_all, 1e-9)
        full['hand.' + s] = hd - fa_ * hd / np.maximum(arm_all, 1e-9)
        full['shoulder_half.' + s] = hs
        # elbow: half-bend bone
        he = np.minimum(2.0 * np.minimum(ua, fa) * o['half_gain'], ua + fa)
        tt = np.maximum(ua + fa, 1e-9)
        ua2 = ua - he * ua / tt; fa2 = fa - he * fa / tt
        full['elbow_half.' + s] = he
        # upper arm twist: swing only at the shoulder -> half the twist mid-arm -> all of it by the elbow
        w_sw = 1.0 - smoothstep(tu, 0.10, 0.50)
        w_full = smoothstep(tu, 0.50, 0.90)
        w_tw = 1.0 - w_sw - w_full
        full['upperarm_sw.' + s] = ua2 * w_sw
        full['upperarm_tw.' + s] = ua2 * w_tw
        full['upperarm.' + s] = ua2 * w_full
        # forearm twist: none at the elbow -> half the hand's twist over the far half (the bracer rides it whole)
        tf = axial(P, el, wr)
        w_ftw = smoothstep(tf, 0.15, 0.50)
        full['forearm_tw.' + s] = fa2 * w_ftw
        full['forearm.' + s] = fa2 * (1.0 - w_ftw)

    # ---- legs: half-bend bone at the knee ------------------------------------------------------------------------------
    for s in 'LR':
        th = full['thigh.' + s]; sn = full['shin.' + s]
        hk = np.minimum(2.0 * np.minimum(th, sn) * o['half_gain'], th + sn)
        tt = np.maximum(th + sn, 1e-9)
        full['thigh.' + s] = th - hk * th / tt; full['shin.' + s] = sn - hk * sn / tt
        full['knee_half.' + s] = hk

    Wb = np.column_stack([full[nme] for nme in names])
    Wb = np.clip(Wb, 0, None)

    # ---- whole mesh: body + sling + stone -----------------------------------------------------------------------------
    Wall = np.zeros((len(mesh.V), len(names)))
    Wall[verts] = Wb
    ni = {nme: i for i, nme in enumerate(names)}
    nodes = rs_skel.sling_nodes(); S = rs_skel.SLING_SEGS
    sv = np.where(mesh.vpart == 1)[0]
    ts = axial(mesh.V[sv], nodes[0], nodes[-1]) * S              # 0..S along the chain
    seg_names = ['sling'] + ['sling.%03d' % i for i in range(1, S)]
    for k in range(S):
        # hat functions centred on each segment's middle; the cup (past the last node's start) rides the last segment
        c = k + 0.5
        w = np.clip(1.0 - np.abs(ts - c), 0.0, 1.0)
        if k == 0: w[ts < c] = 1.0
        if k == S - 1: w[ts > c] = 1.0
        Wall[sv, ni[seg_names[k]]] = w
    Wall[np.where(mesh.vpart == 2)[0], ni['stone']] = 1.0

    Wall = prune(Wall, 4)
    return names, Wall, dict(lab=lab, verts=verts, main_names=main_names, bag=bag, knot=knot, mask=m)


def _blur_scalar(mesh, verts, x, std):
    L, area = mesh.laplacian()
    L = L[verts][:, verts].tocsc(); A = diags(area[verts])
    lu = splu((A + (std * std / 2.0) * L).tocsc())
    return np.clip(lu.solve(area[verts] * x), 0.0, 1.0)


def prune(W, k=4, eps=0.004):
    W = W.copy()
    W[W < eps] = 0.0
    idx = np.argsort(-W, axis=1)[:, k:]
    np.put_along_axis(W, idx, 0.0, axis=1)
    s = W.sum(1, keepdims=True)
    assert (s > 0).all(), 'vertex without weights: %d' % int((s <= 0).sum())
    return W / s
