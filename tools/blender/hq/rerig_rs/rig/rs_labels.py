"""Hard segmentation of the body shell: every vertex belongs to one main bone (smooth blends come later).

Limbs are separated from the trunk by 'nearest bone seen through the inside of the mesh', then cut at their joints by
planes; the head (hair, beard and face) is a semantic mask from the baked colours; trunk props (hip bag, belt knot) ride
the pelvis.
"""
import colorsys
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components, dijkstra
import rs_skel

J = rs_skel.J


def graph(mesh, verts):
    """Adjacency (csr, edge lengths) of the sub-mesh on `verts`, and the global->local index map."""
    loc = np.full(len(mesh.V), -1); loc[verts] = np.arange(len(verts))
    E = mesh.edges
    m = (loc[E[:, 0]] >= 0) & (loc[E[:, 1]] >= 0)
    a, b = loc[E[m, 0]], loc[E[m, 1]]
    w = np.linalg.norm(mesh.V[E[m, 0]] - mesh.V[E[m, 1]], axis=1)
    n = len(verts)
    G = coo_matrix((np.concatenate([w, w]), (np.concatenate([a, b]), np.concatenate([b, a]))), shape=(n, n)).tocsr()
    return G, loc


def largest_component_with(G, mask, seed_mask):
    """Of the connected pieces of `mask`, keep those that contain a seed."""
    idx = np.where(mask)[0]
    sub = G[idx][:, idx]
    nc, lab = connected_components(sub, directed=False)
    keep = np.zeros(len(mask), bool)
    seeds = set(lab[np.where(seed_mask[idx])[0]].tolist())
    keep[idx[np.isin(lab, list(seeds))]] = True
    return keep


def mode_filter(G, lab, nlab, iters=2, frozen=None):
    A = (G > 0).astype(np.float64).tocsr()
    for _ in range(iters):
        onehot = np.zeros((len(lab), nlab)); onehot[np.arange(len(lab)), lab] = 1.0
        votes = A @ onehot + 0.9 * onehot
        new = votes.argmax(1)
        if frozen is not None: new[frozen] = lab[frozen]
        lab = new
    return lab


def head_mask(mesh, verts, col, G):
    """Hair, beard, face and the bones in the hair."""
    P = mesh.V[verts]; C = col[verts]
    hsv = np.array([colorsys.rgb_to_hsv(*c) for c in C])
    dark = hsv[:, 2] < 0.42
    # smooth the darkness so the leopard's spots (small dark blobs in yellow fur) don't count as hair
    A = (G > 0).astype(np.float64).tocsr(); deg = np.asarray(A.sum(1)).ravel()
    s = dark.astype(float)
    for _ in range(6):
        s = 0.5 * s + 0.5 * (A @ s) / np.maximum(deg, 1)
    hairy = (s > 0.5) & (P[:, 2] > 1.12)
    hc = J['head'] + np.array([0.0, -0.03, 0.17])
    e = ((P - hc) / np.array([0.34, 0.40, 0.34])) ** 2
    in_head = e.sum(1) < 1.0
    cand = hairy | in_head
    seed = np.zeros(len(P), bool); seed[np.argmax(P[:, 2])] = True
    seed |= in_head & (P[:, 2] > hc[2])
    head = largest_component_with(G, cand, seed)
    # islands the head encloses (the tip of his nose pokes out of the ellipsoid and is not dark) belong to it too:
    # only the piece of 'not head' that holds the feet is the body
    rest = np.where(~head)[0]
    nc, comp = connected_components(G[rest][:, rest], directed=False)
    body = comp[np.argmin(P[rest, 2])]
    head[rest[comp != body]] = True
    return head, hairy, in_head


def plane_side(P, origin, normal):
    return (P - origin) @ (normal / np.linalg.norm(normal))


def segment(mesh, col, dist, vis, main_names):
    verts = np.where(mesh.vpart == 0)[0]
    P = mesh.V[verts]
    G, loc = graph(mesh, verts)
    nm = {n: i for i, n in enumerate(main_names)}
    # 1. nearest visible main bone (the anchoring of bone heat), unanchored verts filled from their neighbours
    dv = np.where(vis, dist, np.inf)
    near = dv.argmin(1); has = np.isfinite(dv.min(1))
    if (~has).any():
        d, pred, src = dijkstra(G, indices=np.where(has)[0], return_predecessors=True, min_only=True)
        near[~has] = near[src[~has]]
    near = mode_filter(G, near, len(main_names), 3)
    lab = near.copy()
    grp = {}
    for s in 'LR':
        grp['arm.' + s] = np.isin(near, [nm['upperarm.' + s], nm['forearm.' + s], nm['hand.' + s]])
        grp['leg.' + s] = np.isin(near, [nm['thigh.' + s], nm['shin.' + s], nm['foot.' + s], nm['toe.' + s]])
    # 2. each limb is the piece of its group that holds its end; anything else in the group goes back to the trunk
    for s in 'LR':
        tip = np.zeros(len(P), bool); tip[np.argmin(np.linalg.norm(P - J['hand_end.' + s], axis=1))] = True
        grp['arm.' + s] = largest_component_with(G, grp['arm.' + s], tip)
        tip = np.zeros(len(P), bool); tip[np.argmin(np.linalg.norm(P - J['toe_end.' + s], axis=1))] = True
        grp['leg.' + s] = largest_component_with(G, grp['leg.' + s], tip)
    limb = np.zeros(len(P), bool)
    for k in grp: limb |= grp[k]
    # 3. the head
    head, hairy, in_head = head_mask(mesh, verts, col, G)
    head &= ~limb
    # 4. trunk: pelvis / spine / chest by the planes at their joints (leaning with the spine), clavicles by nearness
    trunk = ~limb & ~head
    up = np.array([0.0, 0.0, 1.0])
    lab[trunk] = nm['root']
    lab[trunk & (plane_side(P, J['spine'], J['chest'] - J['pelvis']) > 0)] = nm['spine']
    lab[trunk & (plane_side(P, J['chest'], J['neck'] - J['spine']) > 0)] = nm['chest']
    for s in 'LR':
        sgn = 1.0 if s == 'L' else -1.0
        sh = J['shoulder.' + s]
        c = trunk & (near == nm['clavicle.' + s]) & (P[:, 2] > J['chest'][2] + 0.12)
        lab[c] = nm['clavicle.' + s]
    lab[head] = nm['head']
    # 5. limbs cut at their joints
    for s in 'LR':
        a = grp['arm.' + s]
        sh, el, wr, he = (J[k + s] for k in ('shoulder.', 'elbow.', 'wrist.', 'hand_end.'))
        u1 = (el - sh) / np.linalg.norm(el - sh); u2 = (wr - el) / np.linalg.norm(wr - el); u3 = (he - wr) / np.linalg.norm(he - wr)
        lab[a] = nm['upperarm.' + s]
        lab[a & (plane_side(P, el, u1 + u2) > 0)] = nm['forearm.' + s]
        lab[a & (plane_side(P, wr, u2 + u3) > 0) & (plane_side(P, el, u1 + u2) > 0)] = nm['hand.' + s]
        g = grp['leg.' + s]
        hp, kn, an, ba, te = (J[k + s] for k in ('hip.', 'knee.', 'ankle.', 'ball.', 'toe_end.'))
        v1 = (kn - hp) / np.linalg.norm(kn - hp); v2 = (an - kn) / np.linalg.norm(an - kn)
        lab[g] = nm['thigh.' + s]
        below_knee = plane_side(P, kn, v1 + v2) > 0
        lab[g & below_knee] = nm['shin.' + s]
        # the foot: everything under the ankle's level, and what lies in front of the shin's front below the cuff
        foot = g & below_knee & ((P[:, 2] < an[2] + 0.005) | ((P[:, 1] < an[1] - 0.13) & (P[:, 2] < an[2] + 0.07)))
        lab[foot] = nm['foot.' + s]
        lab[foot & (P[:, 1] < ba[1])] = nm['toe.' + s]
    return verts, lab, dict(G=G, loc=loc, head=head, hairy=hairy, in_head=in_head, grp=grp, trunk=trunk, near=near)
